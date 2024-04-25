import streamlit as st
import altair as alt
import pandas as pd
import panel as pn
from vega_datasets import data
import warnings

# Ignore all warnings
warnings.filterwarnings('ignore')
countries = alt.topo_feature(data.world_110m.url, 'countries')

# Load datasets
values = pd.read_csv("burden-disease-from-each-mental-illness.csv")

# Dataset preprocessing
values.rename(columns={
    'Entity': 'name',
    'Code': 'alpha-3',
    'DALYs from depressive disorders per 100,000 people in, both sexes aged age-standardized': 'Depression',
    'DALYs from schizophrenia per 100,000 people in, both sexes aged age-standardized': 'Schizophrenia',
    'DALYs from bipolar disorder per 100,000 people in, both sexes aged age-standardized': 'Bipolar Disorder',
    'DALYs from eating disorders per 100,000 people in, both sexes aged age-standardized': 'Eating Disorders',
    'DALYs from anxiety disorders per 100,000 people in, both sexes aged age-standardized': 'Anxiety Disorders',
}, inplace=True)
values_all_years = values
quantitative_columns = ['alpha-3','Depression', 'Schizophrenia', 'Bipolar Disorder', 'Eating Disorders', 'Anxiety Disorders']
values.dropna(subset=quantitative_columns, inplace=True)

# Enable Panel extensions
pn.extension()
alt.data_transformers.disable_max_rows()
countries = alt.topo_feature(data.world_110m.url, "countries")  
country_codes = pd.read_csv(
    "https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv"
)

###### First plots ########
def create_plot_first(subgroup, year=2019):
    values_tmp = values[values['Year'] == year]
    # Apply any required transformations to the data in pandas
    background = alt.Chart(countries).mark_geoshape(
        fill="lightgray"
        ).transform_filter(
            alt.datum.id != 10 # Exclude Antarctica from the map
        )

    # we transform twice, first from "ISO 3166-1 numeric" to name, then from name to value
    selection = alt.selection_point(fields=["name"], empty="none")
    opacity_condition = alt.condition(selection, 
                                alt.value(1), 
                                alt.value(0.85))
    stroke_condition = alt.condition(selection,
                                    alt.value("black"),
                                    alt.value("white"))
    stroke_width_condition = alt.condition(selection,
                                    alt.value(1.5),
                                    alt.value(0.1))

    foreground = (
        alt.Chart(countries)
        .mark_geoshape()
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(data=country_codes, key="country-code", fields=["alpha-3"]),
        )
        .transform_lookup(
            lookup="alpha-3",
            from_=alt.LookupData(data=values_tmp, key="alpha-3", fields=["name",f"{subgroup}"]),
        )
        .encode(
            fill=alt.Color(
                f"{subgroup}:Q",
                scale=alt.Scale(scheme="reds"),  # adjust the domain as needed
            ),
            stroke=stroke_condition,
            strokeWidth=stroke_width_condition,
            tooltip=["name:N", f"{subgroup}:Q"],
            opacity=opacity_condition,
        )
    ).properties(
        title=f"{subgroup} per 100,000 people in Year {year}"
    )

    chart = (
        (background + foreground)
        .properties(width=600, height=600)
        .project(
            type="mercator"
        ).add_params(
            selection
        )
    ).properties(
        width = 400,
    )

    pop_bar_chart = (
        alt.Chart(
            values_tmp.nlargest(10, subgroup)
        ).mark_bar().encode(
            x=alt.X(f"{subgroup}:Q", title=f'{subgroup} per 100,000 people'),
            y=alt.Y("name:N", sort='-x'),
            color=alt.Color(f"{subgroup}:Q",scale=alt.Scale(scheme="reds"),legend=None),
            opacity=opacity_condition,
            tooltip=["name:N", f"{subgroup}:Q"],
        ).add_selection(
            selection
        ).properties(
            title=f"Top 10 countries by {subgroup} in Year {year}"
        )
    ).properties(
        width = 200,
        height = 200
    )

    global_trend = (
        alt.Chart(values_all_years)
        .mark_line()
        .encode(
            x=alt.X("Year:O", title='Year'),
            y=alt.Y(f"mean({subgroup}):Q", title=f'Average {subgroup} per 100,000 people'),
            color=alt.value('lightgrey'),  # Use a neutral color like grey for the global line
        )
        .properties(
            title=f"Global and Country-Specific {subgroup} Trend"
        )
    )

    country_trend = (
        alt.Chart(values_all_years)
        .mark_line()
        .encode(
            x=alt.X("Year:O", title='Year'),
            y=alt.Y(f"{subgroup}:Q"),
            color=alt.Color("name:N", scale=alt.Scale(scheme="reds"),legend=None),
            opacity=alt.condition(selection, alt.value(1), alt.value(0))  # Link the selection to the line chart
        )
        .transform_filter(
            selection  # Filter based on the selected country
        )
        .properties(
            title=f"Country-Specific {subgroup} and Trend per 100,000 people"
        )
    )

    line_plot = alt.layer(global_trend, country_trend).add_selection(
        selection
    ).properties(
        width = 200,
        height = 150
    )

    final_visualization = chart | (pop_bar_chart & line_plot)
    final_visualization = final_visualization.configure_title(fontSize=16).configure_legend(offset=0,padding=0,titleFontSize=11, labelFontSize=11)
    return final_visualization
    

##### Second Plots ########
def creat_plot_line_second(df, color_col, title):
    if color_col == 'Race/Ethnicity':
        bar = alt.Chart(df_race).mark_bar(color='#7EA1FF').encode(
        alt.Y('Race/Ethnicity:N', sort='-x', title=None),
        alt.X('percentage:Q', scale=alt.Scale(domain=[0, 0.18])),
        tooltip=alt.Text('percentage:Q', format='.1%', title=None)
        ).properties(
            title=title
        ).configure_axis(
            grid=False
        )
        return bar
    else:
        nearest = alt.selection_point(nearest=True, on='mouseover', fields=['year'], empty=False)
        legend_selection = alt.selection_point(fields=[color_col], bind='legend')

        # Create the base chart and filter to All polls
        line = alt.Chart(df).mark_line(
            interpolate='basis',
            size=2.5
            ).encode(
                x=alt.X('year:N', title=None, axis=alt.Axis(labels=False)),
                y=alt.Y('percentage:Q', axis=alt.Axis(format='%')),
                color=f"{color_col}:N"
            ).properties(
                title=title
            ).add_params(
                legend_selection
            ).transform_filter(
                legend_selection
            )

        # Vertical line
        rules = alt.Chart(df).mark_rule(color='lightgray', size=2).encode(
            x='year:N',
        ).transform_filter(
            nearest
        )

        # interaction dots
        selectors = alt.Chart(df).mark_point().encode(
            x='year:N',
            opacity=alt.value(0),
        ).add_params(
            nearest
        )
        points = line.mark_point(size=90).encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0))
        )

        # interaction text labels
        text = line.mark_text(align='left', dx=7, dy=15, fontSize=14).encode(
            text=alt.condition(nearest, alt.Text('percentage:Q', format='.4f'), alt.value(' '))
        )

        # Put them all together
        final_viz = alt.layer(line, points, selectors, rules, text)
        return final_viz


if __name__ == '__main__':
    st.markdown(
    f"""
    <style>
        .reportview-container .main .block-container{{
            margin-left: {1}rem;
            max-width: {1800}px;
            padding-top: {1}rem;
            padding-bottom: {1}rem;
        }}
        .reportview-container .main {{
            color: white;
            background-color: black;
        }}
    </style>
    """
    ,unsafe_allow_html=True,
    )

    warnings.filterwarnings('ignore')
    countries = alt.topo_feature(data.world_110m.url, 'countries')
    values = pd.read_csv("burden-disease-from-each-mental-illness.csv")
    values.rename(columns={
        'Entity': 'name',
        'Code': 'alpha-3',
        'DALYs from depressive disorders per 100,000 people in, both sexes aged age-standardized': 'Depression',
        'DALYs from schizophrenia per 100,000 people in, both sexes aged age-standardized': 'Schizophrenia',
        'DALYs from bipolar disorder per 100,000 people in, both sexes aged age-standardized': 'Bipolar Disorder',
        'DALYs from eating disorders per 100,000 people in, both sexes aged age-standardized': 'Eating Disorders',
        'DALYs from anxiety disorders per 100,000 people in, both sexes aged age-standardized': 'Anxiety Disorders',
    }, inplace=True)

    values_all_years = values
    quantitative_columns = ['alpha-3','Depression', 'Schizophrenia', 'Bipolar Disorder', 'Eating Disorders', 'Anxiety Disorders']
    values.dropna(subset=quantitative_columns, inplace=True)

    # Enable Panel extensions
    alt.data_transformers.disable_max_rows()
    countries = alt.topo_feature(data.world_110m.url, "countries")   
    country_codes = pd.read_csv(
        "https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv"
    )

######################################################################################################################
    # Displayed Contents
    st.markdown("# Shining a Spotlight on Depression: Urgent Attention Required for this Mental Health Disorder")
    st.markdown('## What is Mental Health Disorders?')
    st.markdown("Mental health problems, also known as mental health disorders or mental illnesses, encompass a wide range of conditions that affect a person's mood, thinking, behavior, and overall psychological well-being. Mental health problems are classified into several categories according to recognized systems such as the Diagnostic and Statistical Manual of Mental Disorders (DSM) and the International Classification of Diseases (ICD). Some common categories include: **Anxiety Disorders**, **Eating Disorders**, **Schizophrenia**, and Trauma and Stressor-Related Disorders and Mood Disorders, which include conditions like **depression** and **bipolar disorder**, characterized by significant disturbances in a person's mood and emotional state.")

    st.markdown('## How Close are We to Confronting Mental Health Disorders?')
    st.markdown(
        "You might think that mental health disorders are not as common as other health problems, but they are actually quite prevalent. According to the World Health Organization (WHO), mental health disorders are the leading cause of disability worldwide. In fact, it is estimated that **one in four people will experience a mental health disorder at some point in their lives**.\n\n Interacting with the figures below, you'll delve into the evolving landscape of mental health disorders across different countries worldwide. The darker the shade of red, the higher the burden of mental health disorders in that country. Upon closer examination, you'll discover that **mental health issues transcend national boundaries and socioeconomic status, affecting individuals from all walks of life**. For instance, in 2019, nine out of the ten countries with the highest rates of depression were developing regions. However, developed countries also face their share of struggles with mental disorders, with the United States leading in schizophrenia rates and Australia grappling with a significant burden of eating disorders. Remarkably, Australia's incidence of eating disorders was three times higher than the global average and has shown a steady increase since 1990. \n\n")

    col1, col2 = st.columns(2)
    with col1:
        subgroup_choice = st.selectbox("Select the disease you would like to explore:", ['Depression', 'Schizophrenia', 'Bipolar Disorder', 'Eating Disorders', 'Anxiety Disorders'])

    with col2:
        year_choice = st.selectbox("Select the year you would like to explore:", [2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 2004, 2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994, 1993, 1992, 1991, 1990])

    st.altair_chart(create_plot_first(subgroup_choice, year_choice), use_container_width=True)


    ######## Second Plot ########
    st.markdown("Different mental disorders may have similarities, but they also differ, such as why people get them or how to treat them. Their prevalence among demographics also varies: some may affect certain age groups or genders more, while others don't show clear patterns. It's hard to talk about all of them in one article, so we're focusing on depression. Looking at the world map above, it seems like all countries have similar dark hue on the depression issue, compared to when we look at *Eating DIsorders*, only Australia and North America stand out. This suggests that depression is a big problem everywhere. We are hoping to populate basic trend about depression, so as to bring this bitable issue to more people's attention and help people support their families or friends who might be experiencing it.")

    st.markdown('## What Groups are Vulnerable to Depression?')
    st.markdown("To focus our discussion, we specifically examine depression in the United States. Statistics reveal that **women are nearly twice as likely as men to receive a depression diagnosis**. This trend may stem from hormonal fluctuations during puberty and significant life changes such as pregnancy. Girls typically mature earlier than boys and tend to be more emotionally sensitive, suggesting that this depression gap persists throughout lifespan.Furthermore, while depression can occur at any age, it appears to be more prevalent among younger demographics. **Adolescents aged 12-17 exhibit the highest rates of depression**, with a rising trend, followed by young adults aged 18 to 25 who may just get out of school and navigate lives on their own. Conversely, elderly individuals, with fewer social and work-related pressures, have the lowest rates of depression. Additionally, financial stability plays a role in mental health. **Individuals with a higher Poverty-Income Ratio (PIR) are less susceptible to depression than those with lower PIRs**. Moreover, the incidence of depression varies across different racial and ethnic groups. **Individuals of mixed racial backgrounds are particularly vulnerable to depression**, with Native American/American Indian and White individuals following closely.")

    st.markdown("The chart below shows how depression impacts various demographic groups, including age, race, income level, and gender. While we focus on male and female genders to ensure data consistency from 1990 to 2019, it's important to note that LGBTQ+ individuals often experience higher rates of depression, influenced by societal pressures and familial dynamics. Also, due to the proximity of some data points, the value labels may overlap. To address this issue, you can click on a specific field in the legend to isolate it on the plot.")

    df_gender = pd.read_csv('depression_by_gender.csv')
    df_age = pd.read_csv('depression_age.csv')
    df_income = pd.read_csv('depression_income.csv')
    df_race = pd.read_csv('depression_race.csv')
    df_gender['percentage'] = df_gender['percentage'].str.rstrip('%').astype(float) / 100
    df_age['percentage'] = df_age['percentage'].str.rstrip('%').astype(float) / 100
    df_income['percentage'] = df_income['percentage'].str.rstrip('%').astype(float) / 100
    dict_map = {'Gender': [df_gender, "Percentage of U.S. Population that had Depression from 1990 to 2019 by Gender"],
                 'Age': [df_age, "Percentage of U.S. Population that had Depression from 2009 to 2017 by Age"],
                 'Income': [df_income, "Percentage of U.S. Population that had Depression from 2006 to 2016 by PIR"],
                 'Race/Ethnicity': [df_race, 'Percentage of U.S. Population that had Depression by Race/Ethnicity in 2021']}
    
    aspect_type = st.selectbox("Select a factor to break down:", ['Gender', 'Age', 'Income', 'Race/Ethnicity'])
    st.altair_chart(creat_plot_line_second(dict_map[aspect_type][0], aspect_type, dict_map[aspect_type][1]), use_container_width=True)

    st.markdown("Understanding which groups are more vulnerable to depression allows us to prioritize support for those individuals, such as our mothers, sisters, and girlfriends. For parents, it's crucial to monitor the mental well-being of your teenage children and provide them with the care and attention they need. If you belong to one of these vulnerable groups, remember to stay positive and persevere through temporary low points in life. You got this!")

    ######## Third Plot #########
    st.markdown('## Depression can Still be Cured')
    st.markdown("Or other topics")


    ####### References ###########
    st.write("")
    st.write("")
    st.markdown('#### References')
    st.markdown("[1]. Zare, Hossein et al. “How Income and Income Inequality Drive Depressive Symptoms in U.S. Adults, Does Sex Matter: 2005-2016.” International journal of environmental research and public health vol. 19,10 6227. 20 May. 2022, doi:10.3390/ijerph19106227. [Apr.25, 2024]")
    st.markdown("[2]. 'Major Depression.' *National Institute of Mental Health*, https://www.nimh.nih.gov/health/statistics/major-depression#part_2567. [Apr.24, 2024]")
    st.markdown("[3]. 'Percentage of People in the U.S. who suffered from depression from 1990 to 2019 by gender.' *statista*, https://www.statista.com/statistics/979898/percentage-of-people-with-depression-us-by-gender. [Apr.24, 2024]")
    st.markdown("[4]. Twenge, Jean, et.al. 'Age, Period, and Cohort Trends in Mood Disorder Indicators and Suicide-Related Outcomes in a Nationally Representative Datasets, 2005-2017.' *American Psychological Association*, https://www.apa.org/pubs/journals/releases/abn-abn0000410.pdf. [Apr.24, 2024]")
