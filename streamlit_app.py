import streamlit as st

from app_runtime import CANONICAL_V1_DESCRIPTION, analyze_repository, GitHubAPIError

def main():
    st.set_page_config(
        page_title="AI Fake Project Detector (Demo)",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 AI Fake Project Detector · Demo Surface")
    st.caption(f"Canonical V1 runtime: {CANONICAL_V1_DESCRIPTION} in flask_app.py")
    st.warning(
        "This Streamlit entrypoint is demo/dev-only and must not be treated as "
        "the primary V1 product surface."
    )
    st.markdown("""
    Use this local companion UI only for exploration. Production-shaped web/API
    behavior lives in the Flask surface.
    """)
    
    # Input for GitHub URL
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repo",
        help="Enter a public GitHub repository URL to analyze"
    )
    
    # Analyze button
    if st.button("Analyze Repository"):
        if not repo_url:
            st.warning("Please enter a GitHub repository URL")
            return
        
        # Show loading spinner
        with st.spinner("Analyzing repository..."):
            try:
                st.info("Running the canonical Flask analysis flow...")
                analysis_data = analyze_repository(repo_url)
                repo_data = analysis_data["repo_info"]
                result = analysis_data["scoring_result"]
                 
                # Display results
                st.success("Analysis complete!")
                
                # Create columns for layout
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.metric(
                        label="Fake Risk Score",
                        value=f"{result['fake_risk_score']}/100",
                        delta=None
                    )
                    st.markdown(f"**Risk Level:** {result['risk_level'].upper()}")
                    
                    # Risk level color
                    risk_color = {
                        "low": "green",
                        "medium": "orange",
                        "high": "red",
                        "extreme": "darkred"
                    }.get(result['risk_level'], "gray")
                    
                    st.markdown(
                        f"<div style='background-color: {risk_color}; "
                        f"color: white; padding: 10px; border-radius: 5px; "
                        f"text-align: center;'>{result['risk_level'].upper()}</div>",
                        unsafe_allow_html=True
                    )
                
                with col2:
                    st.subheader("Dimension Scores")
                    dims = result['dimension_scores']
                    # Create a bar chart for dimension scores
                    st.bar_chart({
                        "Delivery (30)": dims['delivery'],
                        "Substance (20)": dims['substance'],
                        "Evidence (15)": dims['evidence'],
                        "Peer Gap (15)": dims['peer_gap'],
                        "Community (10)": dims['community'],
                        "Hype Gap (10)": dims['hype_gap']
                    })
                
                # Display evidence cards
                st.subheader("Evidence Cards")
                for i, card in enumerate(result['evidence_cards']):
                    with st.expander(f"Evidence {i+1}: {card['description']}"):
                        st.write(f"**Value:** {card['value']}")
                        st.write(f"**Threshold:** {card['threshold']}")
                        st.write(f"**Passed:** {'✅' if card['passed'] else '❌'}")
                
                # Display guardrail notes
                st.subheader("Important Notes")
                for note in result['guardrail_notes']:
                    st.info(note)
                
                # Display peer baseline summary
                st.subheader("Baseline Comparison")
                st.write(result['peer_baseline_summary'])
                
                # Display repository info
                with st.expander("Repository Information"):
                    st.json({
                        "Repository": f"{repo_data['owner']}/{repo_data['name']}",
                        "Description": repo_data['description'],
                        "Stars": repo_data['stars'],
                        "Forks": repo_data['forks'],
                        "Language": repo_data['language'],
                        "Size (KB):": repo_data['size_kb'],
                        "Created At": repo_data['created_at'],
                        "Updated At": repo_data['updated_at']
                    })
                
            except ValueError as e:
                st.error(f"Input error: {str(e)}")
            except GitHubAPIError as e:
                st.error(f"GitHub API error: {str(e)} (Status code: {e.status_code})")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()
